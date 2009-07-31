from twisted.web import resource, server
from twisted.web.static import File
from manager import ClientDelegate

class APIRoot(resource.Resource):
    def __init__(self, manager):
        resource.Resource.__init__(self)
        self.putChild('', File('media/index.html'))
        self.putChild('jquery-1.3.2.min.js', File('media/jquery-1.3.2.min.js'))
        self.putChild('jquery.corners.min.js', File('media/jquery.corners.min.js'))
        self.putChild('post', NotificationPoster(manager))
        self.putChild('listen', NotificationRequester(manager))
        self.putChild('checkpasswd', PasswordCheckerResource(manager))
    

class NotificationPoster(resource.Resource):
    isLeaf = True

    def __init__(self, manager):
        resource.Resource.__init__(self)
        self.manager = manager

    def render_POST(self, request):
        if not self.manager.checkCredentials(request):
            return "{'success': false, 'message': 'Invalid Credentials'}"
	print request.args
        if 'notificationText' not in request.args:
            return "{'success': false, 'message': 'Blank notifications are not allowed'}"
        text = request.args['notificationText']
        print "Notifying clients for user", request.getUser()
        self.manager.notifyDelegates(request.getUser(), '{ "success" : "true", "message" : "' + text[0] + '" }')
        return "{'success': 'true', 'message': 'Notification Sent Successfully'}"


class NotificationRequester(resource.Resource):
    isLeaf = True

    def __init__(self, manager):
        resource.Resource.__init__(self)
        self.manager = manager
    
    def render_GET(self, request):
        print "Delegate Request Received"
        if not self.manager.checkCredentials(request):
            return "{'success': false, 'message': 'Invalid Credentials'}"
        self.manager.addDelegate(request.getUser(), ClientDelegate(request))
        return server.NOT_DONE_YET


class PasswordCheckerResource(resource.Resource):
    isLeaf = True

    def __init__(self, manager):
        resource.Resource.__init__(self)
        self.manager = manager
    
    def render_GET(self, request):
        if self.manager.checkCredentials(request):
            return "{'success': true}"
        else:
            return "{'success': false}"
