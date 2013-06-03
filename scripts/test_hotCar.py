import test_setup
import hotCarApp


def runTest():
    hotCarApp.runOnce()

def runTestGreenlet():
    G = hotCarApp.HotCarApp()
    print 'Starting Hot Car App!'
    G.start()
    print 'Hot Car App Started!'
    G.join()
    print 'Hot Car Happ finished!'

    
def run():
    test_setup.startup()
    runTestGreenlet()
    #runTest()
    test_setup.shutdown()

if __name__ == '__main__':
    run()
