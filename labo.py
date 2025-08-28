import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)

choix = input("ON pour allumer, OFF pour eteindre :")

if choix.upper() == "ON":
    GPIO.output(17, GPIO.HIGH)
    print("Lumiere ouverte")
elif choix.upper() == "OFF":
    GPIO.output(17, GPIO.LOW)