import csv
from rapidsms.models import Contact, Backend, Connection
from rapidsms.contrib.ajax.utils import call_router

def send_bulk_message_from_csv(path, text='coffee'):
    backend_name = "TLS-TT"
    file = open(path)
    for line in file:
        line_list = line.split(',')
        name = line_list[0].strip()
        identity = line_list[1].strip()        
#        if Connection.objects.filter(identity=identity).count() == 0:
        contact = Contact(name=name)
        contact.save()
        # TODO deal with errors!
        backend = Backend.objects.get(name=backend_name)
        connection = Connection(backend=backend, identity=identity,\
            contact=contact)
        connection.save()
#       else:
#            connection = Connection.objects.get(identity=identity)
        post = {"connection_id": unicode(connection.id), "text": text}
        call_router("messaging", "send_message", **post)