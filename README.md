# FromShellToNtSystem

<h1>How to send executables over a Telnet Shell</h1>

This script was created in order to gain control over a Windows 2003 Server that had an unsecurized Telnet Accedd.
To do so, i had to encode in base64 my payload before sending it and sending a VB Script that would decode the base64 encoded executable.

I was then able to launch the payload and gain NT System privilegies.
