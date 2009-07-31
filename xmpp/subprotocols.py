from twisted.words.protocols.jabber.xmlstream import toResponse
from twisted.words.xish import domish
from twisted.web import http
from wokkel import xmppim
from wokkel.subprotocols import XMPPHandler

class PresenceAcceptingHandler(xmppim.PresenceProtocol):
    """
    Presence accepting XMPP subprotocol handler.

    This handler blindly accepts incoming presence subscription requests,
    confirms unsubscription requests and responds to presence probes.

    Note that this handler does not remember any contacts, so it will not
    send presence when starting.
    """
    def subscribedReceived(self, presence):
        """
        Subscription approval confirmation was received.

        This is just a confirmation. Don't respond.
        """
        print "Subscribed Received"
        pass


    def unsubscribedReceived(self, presence):
        """
        Unsubscription confirmation was received.

        This is just a confirmation. Don't respond.
        """
        print "Unsubscribed Received"
        pass


    def subscribeReceived(self, presence):
        """
        Subscription request was received.

        Always grant permission to see our presence.
        """
        print "Subscribe Request Received"
        self.subscribed(recipient=presence.sender,
                        sender=presence.recipient)
        self.available(recipient=presence.sender,
                       status=u"I'm here",
                       sender=presence.recipient)


    def unsubscribeReceived(self, presence):
        """
        Unsubscription request was received.

        Always confirm unsubscription requests.
        """
        print "Unsubscribe Request Received"
        self.unsubscribed(recipient=presence.sender,
                          sender=presence.recipient)



    def probeReceived(self, presence):
        """
        A presence probe was received.

        Always send available presence to whoever is asking.
        """
        print "Probe Received"
        self.available(recipient=presence.sender,
                       status=u"I'm here",
                       sender=presence.recipient)



class EchoHandler(xmppim.MessageProtocol):
    """
    Message echoing XMPP subprotocol handler.
    """

    def onMessage(self, message):
        """
        Called when a message stanza was received.
        """
        print "Message Received"

        # Ignore error messages
        if message.getAttribute('type') == 'error':
            return

        # Echo incoming messages, if they have a body.
        if message.body and unicode(message.body):
            response = toResponse(message, message.getAttribute('type'))
            response.addElement('body', content=unicode(message.body))
            self.send(response)


class UserNotifier(XMPPHandler):
    """
    A bloated multi-purpose XMPPHandler for doing almost everything in this
    application. Eventually this should be split out into a user database
    class with separate handler's for different varieties of work.

    Random TODO: Handle Probes
    """
    def __init__(self, address):
        self._address = address
        self._pendingSubscriptions = {}
        self._authDB = {'russell': ('testing', 'russellhaering@gmail.com', True),}
        XMPPHandler.__init__(self)

    def connectionInitialized(self):
        """
        Initialize Observers
        """
        self.xmlstream.addObserver('/presence', self.onPresenceReceived)

    def connectionMade(self):
        """
        Let me know that the server is online
        """
        print "Sending test notification"
        self.notifyUser('russell', Notification(self._address, 'Notiserv2', 'Online', 'Notiserv2 is Online'))

    def notifyUser(self, user, notification):
        """
        Compose and send a notificaiton message only if the jid has been validated
        """
        if self._authDB[user][2]:
            message = domish.Element((None, 'message'))
            message['to'] = self._authDB[user][1]
            message['from'] = user + '@' + self._address
            message.addChild(notification)
            self.send(message)
            return True
        else:
            return False

    def registerUser(self, user, passwd, jid):
        """
        Add the user to the authDB with their jid marked as unvalidated, then send a
        presence subscription request as a means of validation
        """
        if user in self._authDB:
            return False
        else:
            self._authDB[user] = (passwd, jid, False)
            self._pendingSubscriptions[jid] = user
            request = domish.Element((None, 'presence'))
            request['from'] = user + '@' + self._address
            request['to'] = jid
            request['type'] = 'subscribe'
            self.send(request)

    def onPresenceReceived(self, presence):
        """
        Handle incoming presences.

        Notable Cases:
            1. We have a pending presence subscription to that user, and it is
               returned successful. Mark jid validated, send welcome notification.
            2. We have a pending presence subscription to that user and it is
               returned unsuccessful. Leave jid invalid, remove pending status.
            3. Unsubscribed notification for a validated jid. The jid should be
               marked unvalidated. UNHANDLED, TODO
            ...Others...
        """
        if presence.getAttribute('type') == 'subscribed' and presence.getAttribute('from') in self._pendingSubscriptions:
            jid = presence.getAttribute('from')
            user = self._pendingSubscriptions[jid]
            del self._pendingSubscriptions[jid]
            self._authDB[user][2] = True
            self.notifyUser(user,
                            Notification(self._address, 
                                         'Notiserv2',
                                         'Success!',
                                         'You have successfully registered with Notiserv2, get ready for AWESOME!'))
        elif presence.getAttribute('type') == 'unsubscribed' and presence.getAttribute('from') in self._pendingSubscriptions:
            del self._pendingSubscriptions[presence.getAttribute('from')]

    def checkCredentials(self, request):
        """
        HTTP Helper Crap
        """
        user, passwd = request.getUser(), request.getPassword()
        if user in self._authDB and self._authDB[user][0] == passwd:
            return True
        else:
            request.setHeader('WWW-Authenticate', 'Basic realm="NotiServ2 API"')
            request.setResponseCode(http.UNAUTHORIZED)
            return False

class Notification(domish.Element):
    def __init__(self, host, app, summary, body):
        domish.Element.__init__(self, (None, 'notification'))
        self['host'] = host
        self['source'] = app
        self.addElement('summary', content=summary)
        self.addElement('body', content=body)
