import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)
GPIO.setup(4, GPIO.OUT)
GPIO.setup(27, GPIO.OUT)

choix = input("Entrer votre choix en couleur  ")

if choix.upper() == "VERT":
    GPIO.output(17, GPIO.HIGH)
    print("Lumiere ouverte")
    GPIO.output(4, GPIO.LOW)

elif choix.upper() == "ROUGE":
    GPIO.output(4, GPIO.HIGH)
    print("Lumiere ouverte")
    GPIO.output(17, GPIO.LOW)
    
elif choix.upper() == "DEUX":
    GPIO.output(4, GPIO.HIGH)
    print(" les Lumieres  sont ouverte")
    GPIO.output(17, GPIO.HIGH)
elif choix.upper() == "TROIS":
    GPIO.output(4, GPIO.LOW)
    print(" les Lumieres  sont eteinte")
    GPIO.output(17, GPIO.LOW)
