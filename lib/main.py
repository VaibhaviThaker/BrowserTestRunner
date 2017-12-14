import os, sys, requests, retrying, json

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

from lib import selenium_process, log


def Main( seleniumServer = None, testsUrl = None, platform = None, browser = None, browserVersion = None, screenResolution = None,
          framework = None, maxDuration = None, tunnelId = None, output = None, nosandbox = None, prerunScriptUrl = None ):

  driver = None
  framework = __import__( "lib.frameworks." + framework, fromlist = [ "lib.frameworks" ] )

  if ( seleniumServer is None ):

    log.writeln( "Starting selenium ..." )

    seleniumServer = selenium_process.run_selenium_process()
    waitSeleniumPort( seleniumServer )

  try:

    driver_browser = getattr( webdriver.DesiredCapabilities, browser.upper() )

    if not ( nosandbox is None ):
      driver_browser[ "chromeOptions" ] = { "args": [ "--no-sandbox" ] }

    if not ( browserVersion is None ):
      driver_browser[ "version" ] = browserVersion

    if not ( screenResolution is None ):
      driver_browser[ "screenResolution" ] = screenResolution

    if not ( platform is None ):
      driver_browser[ "platform" ] = platform

    if not ( maxDuration is None ):
      driver_browser[ "maxDuration" ] = maxDuration

    if not ( tunnelId is None ):
      driver_browser[ "tunnelIdentifier" ] = tunnelId

    if not ( prerunScriptUrl is None ):
      driver_browser[ "prerun" ] = { "executable": prerunScriptUrl, "background": "false" }

    log.writeln( "Connecting to selenium ..." )

    driver = webdriver.Remote( seleniumServer, driver_browser )
    driver.set_page_load_timeout( 60 )

    log.writeln( "Selenium session id: %s" % ( driver.session_id ) )

    runTests( driver = driver, url = testsUrl, timeout = maxDuration, framework = framework, output = output )

  finally:

    if driver:
      driver.quit()

    selenium_process.stop_selenium_process()

@retrying.retry( stop_max_attempt_number = 2, wait_fixed = 1000, retry_on_result = lambda status: status != 200 )
def waitSeleniumPort( url ):

  return requests.get( url ).status_code

def runTests( driver = None, url = None, timeout = None, framework = None, output = None ):

  log.writeln( "Running tests ..." )

  results = framework.RunTests( driver, url, timeout )
  printResults( results[ "json" ] )

  if ( output ):

    saveResults( results[ "junit" ], output )
    log.writeln( "JUnit xml saved to: " + output )

def saveResults( xmlResults, outputFile ):

  outputPath = os.path.dirname( outputFile )

  if not os.path.exists( outputPath ):
    os.makedirs( outputPath )

  f = open( outputFile, "wb" )
  f.write( xmlResults.encode( "utf-8" ) )
  f.close()

def printResults( results ):

  log.writeln( "Results:" )
  log.writeln( "  Passed: %r" % results[ "passed" ] )
  log.writeln( "  Duration: %f" % results[ "durationSec" ] )
  log.writeln( "  Suites: %d" % len( results[ "suites" ] ) )
