import test_setup
test_setup.startup()

import hotCarApp

def runTest():
    hotCarApp.runOnce()

def runTestGreenlet():
    G = hotCarApp.HotCarApp(LIVE=False)
    print 'Starting Hot Car App!'
    G.start()
    print 'Hot Car App Started!'
    G.join()
    print 'Hot Car Happ finished!'

    
def run():
    runTestGreenlet()
    #runTest()
    test_setup.shutdown()

if __name__ == '__main__':
    run()
