from smtpd import DebuggingServer
import asyncore

server = DebuggingServer(("localhost", 2525), None)
asyncore.loop()

