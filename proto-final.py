import time
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(4, GPIO.OUT)
GPIO.setup(17, GPIO.OUT)
GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP)
testTemps =  0

GPIO.output(17, GPIO.LOW)
GPIO.output(4, GPIO.LOW)
while True :
    etat = GPIO.input(27)
    if etat == 0:
        testTemps = testTemps +1
        print("bouton appuye ")     
    elif etat == 1 :
            print(" bouton non appuyer")
            if testTemps == 1:
                print("bouton appuye vert allumer")     
                GPIO.output(17, GPIO.HIGH)
                GPIO.output(4, GPIO.LOW)
            elif testTemps == 3:
                print("bouton  appuye lumiere rouge")
                GPIO.output(4, GPIO.HIGH)
                GPIO.output(17, GPIO.LOW)
            elif  testTemps == 5:
                GPIO.output(4, GPIO.LOW)
                GPIO.output(17, GPIO.LOW)
                print("bouton  eteint")
            testTemps =  0
    time.sleep(1)
    
