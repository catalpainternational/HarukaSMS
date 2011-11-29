import time
import copy
import Queue
import urllib
import urllib2
import logging
import threading

import pygsm

logger = logging.getLogger('pygsm_gateway.gsm')


class GsmPollingThread(threading.Thread):
    _title = "pyGSM"

    # number of seconds to wait between
    # polling the modem for incoming SMS
    POLL_INTERVAL = 5

    # time to wait for the start method to
    # complete before assuming that it failed
    MAX_CONNECT_TIME = 10

    def __init__(self, url, url_args, modem_args):
        self.url = url
        self.url_args = url_args
        self.modem_kwargs = modem_args
        self.modem = None

        # set a default timeout if it wasn't specified in localsettings.py;
        # otherwise read() will hang forever if the modem is powered off
        if "timeout" not in self.modem_kwargs:
            self.modem_kwargs["timeout"] = '10'
        super(GsmPollingThread, self).__init__()


    def _wait_for_modem(self):
        """
        Blocks until this backend has connected to and initialized the modem,
        waiting for a maximum of self.MAX_CONNECT_TIME (default=10) seconds.
        Returns true when modem is ready, or false if it times out.
        """

        # if the modem isn't present yet, this message is probably being sent by
        # an application during startup from the main thread, before this thread
        # has connected to the modem. block for a short while before giving up.
        for n in range(0, self.MAX_CONNECT_TIME*10):
            if self.modem is not None: return True
            time.sleep(0.1)

        # timed out. we're still not connected
        # this is bad news, but not fatal, so warn
        logger.warning("Timed out while waiting for modem")
        return False


    def get_inbox_size(self,):
        """
        For figuring out message box size
        """

        boxdata = self.modem.query('AT+CMGD=?')
        
        if "error" in boxdata.lower():
            print "Error - phone not supported"
            exit()
        #import pdb; pdb.set_trace()
        boxsize = boxdata.split("(")[1].split(")")[0].split("-")[0].split(',').__len__()
        
        logger.debug('SIM Inbox size URL: %s' % boxsize)
        
        return boxsize
    

    def clean_up_inbox(self,):
        """ 
        Clean up routine
        """

        for i in range(self.get_inbox_size()):
            try:
                temp = self.modem.command('AT+CMGR=' + str(i+1)+',1')
                if "REC READ" in temp[0]:
                    self.modem.query('AT+CMGD=' + str(i+1))
                logger.debug('Cleaned messages from inbox')
            except:
                pass


    def send(self, identity, text):

        # if this message is being sent from the start method of
        # an app (which is run in the main thread), this backend
        # may not have had time to start up yet. wait for it
        if not self._wait_for_modem():
            return False

        # attempt to send the message
        # failure is bad, but not fatal
        if str(identity).startswith('+') == False:
            identity = '+' + str(identity)
        was_sent = self.modem.send_sms(str(identity), text)

        if was_sent:
            self.sent_messages += 1
        else:
            self.failed_messages += 1

        return was_sent

    def message(self, identity, text):
        """ handle SMS from modem """
        url_args = copy.copy(self.url_args)
        url_args['identity'] = identity
        url_args['text'] = text

        # For compatibility with rapidsms-httprouter
        url_args['backend'] = 'console'
        url_args['sender'] = identity
        url_args['message'] = text

        try:
            # First we try a GET for httprouter
            logger.debug('Opening URL: %s' % self.url)
            response = urllib2.urlopen(self.url + '/?' + urllib.urlencode(url_args)) # This does a GET and likes httprouter
        except urllib2.HTTPError:
            # If that doesn't work we try a POST for threadless
            try:
                response = urllib2.urlopen(self.url, urllib.urlencode(url_args)) # This does a POST and likes threadlessrouter
            except Exception, e:
                logger.exception(e)
                return False
        except Exception, e:
            logger.exception(e)
            return False
        logger.info('SENT')
        logger.debug('response: %s' % response.read())

    def gsm_log(self, modem, str, level):
        logger.debug("%s: %s" % (level, str))

    def status(self):

        # abort if the modem isn't connected
        # yet. there's no status to fetch
        if not self._wait_for_modem():
            return None

        csq = self.modem.signal_strength()

        # convert the "real" signal
        # strength into a 0-4 scale
        if   not csq:   level = 0
        elif csq >= 30: level = 4
        elif csq >= 20: level = 3
        elif csq >= 10: level = 2
        else:           level = 1

        vars = {
            "_signal":  level,
            "_title":   self.title,
            "Messages Sent": self.sent_messages,
            "Messages Received": self.received_messages }

        # pygsm can return the name of the network
        # operator since b19cf3. add it if we can
        if hasattr(self.modem, "network"):
            vars["Network Operator"] = self.modem.network

        return vars

    def start(self):
        try:
            self.sent_messages = 0
            self.failed_messages = 0
            self.received_messages = 0

            logger.info("Connecting and booting via pyGSM...")
            self.modem = pygsm.GsmModem(logger=self.gsm_log,
                                        **self.modem_kwargs)
            self.modem.boot()

            # Clean up (delete) all read messages from the SIM so it doesn't get filled up.
            #Not sure if this is the best place for it
            self.clean_up_inbox()

            if getattr(self, 'service_center', None) is not None:
                self.modem.service_center = self.service_center
        except:
            logger.exception('Caught exception booting modem')
            self.stop()
            raise

        # Now that the modem has been booted, start the thread
        super(GsmPollingThread, self).start()

    def run(self):
        try:
            self.running = True
            while self.running:
                logger.info("Polling modem for messages")
                msg = self.modem.next_message()
    
                if msg is not None:
                    self.received_messages += 1
    
                    # we got an sms! hand it off to the
                    # router to be dispatched to the apps
                    x = self.message(msg.sender, msg.text)
    
                # wait for POLL_INTERVAL seconds before continuing
                # (in a slightly bizarre way, to ensure that we abort
                # as soon as possible when the backend is asked to stop)
                for n in range(0, self.POLL_INTERVAL*10):
                    if not self.running: return None
                    time.sleep(0.1)
        except:
            logger.exception('Caught exception in GSM polling loop')
            raise
        finally:
            self.stop()

        logger.info("Run loop terminated.")

    def stop(self):

        self.running = False

        # disconnect from modem
        if self.modem is not None:
            self.modem.disconnect()
