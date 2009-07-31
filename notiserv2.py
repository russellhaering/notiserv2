"""
An XMPP echo server as a standalone server via s2s.

This echo server accepts and initiates server-to-server connections using
dialback and listens on C{127.0.0.1} with the domain C{localhost}. It will
accept subscription requests for any potential entity at the domain and
send back messages sent to it.
"""

import sys
import os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(HERE)
sys.path.append(os.path.join(HERE, 'wokkel'))

from twisted.application import service, strports
from twisted.words.protocols.jabber.xmlstream import toResponse
from wokkel import component, server, xmppim
from xmpp.subprotocols import PresenceAcceptingHandler, EchoHandler, UserNotifier, Notification

# Configuration parameters

S2S_PORT = 'tcp:5269:interface=0.0.0.0'
SECRET = 'thisisupersecret'
DOMAIN = 'xmpp.russellhaering.com'
LOG_TRAFFIC = True

# Set up the Twisted application

application = service.Application("Notiserv2")

router = component.Router()

serverService = server.ServerService(router, domain=DOMAIN, secret=SECRET)
serverService.logTraffic = LOG_TRAFFIC

s2sFactory = server.XMPPS2SServerFactory(serverService)
s2sFactory.logTraffic = LOG_TRAFFIC

s2sService = strports.service(S2S_PORT, s2sFactory)
s2sService.setServiceParent(application)

echoComponent = component.InternalComponent(router, DOMAIN)
echoComponent.logTraffic = LOG_TRAFFIC
echoComponent.setServiceParent(application)

# This is mostly implemented in the UserNotifier
#presenceHandler = PresenceAcceptingHandler()
#presenceHandler.setHandlerParent(echoComponent)

notifier = UserNotifier(DOMAIN)
notifier.setHandlerParent(echoComponent)

# Keep the EchoHandler around for shits and giggles for now
echoHandler = EchoHandler()
echoHandler.setHandlerParent(echoComponent)
