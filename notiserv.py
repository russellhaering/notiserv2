# First Fix the PYTHONPATH
import sys
from os.path import abspath, dirname
sys.path.append(dirname(abspath(__file__)))

# Now Perform the main imports
from twisted.application import internet, service 
from twisted.web import server, resource
from twisted.web.static import File
from twisted.web.vhost import NameVirtualHost
from api.resources import APIRoot
from api.manager import ClientManager
from website.resources import SiteRoot


manager = ClientManager()
api = APIRoot(manager)
web = SiteRoot() 
vhostManager = NameVirtualHost()
vhostManager.addHost('api.notiserv.org', api)
vhostManager.addHost('notiserv.org', web)
vhostManager.addHost('www.notiserv.org', web)
site = server.Site(vhostManager)
application = service.Application('notiserv') 

siteServer = internet.TCPServer(9100, site)

siteServer.setServiceParent(application)
