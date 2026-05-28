//upload to RedBot mainboard connected to Raspberry Pi via usb

#include <Servo.h>
Servo sweep;

#define    L_CTRL1   2
#define    L_CTRL2   4
#define    L_PWM     5

#define    R_CTRL1   7
#define    R_CTRL2   8
#define    R_PWM     6

int counter = 0;
int antidrift = 0;
const int trig = A2;
const int echo = A3;
int duration;
int distance;

int readDist(int servoDeg, int pause) { //negative servoDeg if you don't want to move the servo

  if (servoDeg >= 0) {
    sweep.write(servoDeg);
  }

  delay(pause);

  digitalWrite(trig, LOW);
  delayMicroseconds(2);
  digitalWrite(trig, HIGH);
  delayMicroseconds(10);
  digitalWrite(trig, LOW);
  duration = pulseIn(echo, HIGH);
  distance = duration * 0.0343 / 2;
  Serial.print("#PAIR ");
  Serial.print(sweep.read()*3.14159/180);
  Serial.print(",");
  Serial.println(distance);
}

int freeRam () {
  extern int __heap_start, *__brkval;
  int v;
  return (int) &v - (__brkval == 0 ? (int) &__heap_start : (int) __brkval);
}

void setup()
{
    pinMode(L_CTRL1, OUTPUT);  // used as a debug pin for an LED.
    pinMode(L_CTRL2, OUTPUT);  // used as a debug pin for an LED.
    pinMode(L_PWM, OUTPUT);  // used as a debug pin for an LED.

    pinMode(R_CTRL1, OUTPUT);  // used as a debug pin for an LED.
    pinMode(R_CTRL2, OUTPUT);  // used as a debug pin for an LED.
    pinMode(R_PWM, OUTPUT);  // used as a debug pin for an LED.

    pinMode(13, OUTPUT);  // used as a debug pin for an LED.
    digitalWrite(13, HIGH);

    Serial.begin(9600);

    pinMode(trig, OUTPUT);
    pinMode(echo, INPUT);
    pinMode(12, INPUT_PULLUP);
    
    sweep.attach(A0);
    sweep.write(90);

    readDist(90, 100);

    
}



void leftMotor(int motorPower)
{
    motorPower = constrain(motorPower, -255, 255);   // constrain motorPower to -255 to +255
    if(motorPower >= 0)
    {
        // spin CW
        digitalWrite(L_CTRL1, HIGH);
        digitalWrite(L_CTRL2, LOW);
        analogWrite(L_PWM, abs(motorPower));
    }
    else
    {
        // spin CCW
        digitalWrite(L_CTRL1, LOW);
        digitalWrite(L_CTRL2, HIGH);
        analogWrite(L_PWM, abs(motorPower));
    }
}

/*******************************************************************************/
void rightMotor(int motorPower)
{
    motorPower = constrain(motorPower, -255, 255);   // constrain motorPower to -255 to +255
    if(motorPower >= 0)
    {
        // spin CW
        digitalWrite(R_CTRL1, HIGH);
        digitalWrite(R_CTRL2, LOW);
        analogWrite(R_PWM, abs(motorPower));
    }
    else
    {
        // spin CCW
        digitalWrite(R_CTRL1, LOW);
        digitalWrite(R_CTRL2, HIGH);
        analogWrite(R_PWM, abs(motorPower));
    }
}



/*******************************************************************************/
void leftBrake()
{
    // setting both controls HIGH, shorts the motor out -- causing it to self brake.
    digitalWrite(L_CTRL1, HIGH);
    digitalWrite(L_CTRL2, HIGH);
    analogWrite(L_PWM, 0);
}

/*******************************************************************************/
void rightBrake()
{
    // setting both controls HIGH, shorts the motor out -- causing it to self brake.
    digitalWrite(L_CTRL1, HIGH);
    digitalWrite(L_CTRL2, HIGH);
    analogWrite(R_PWM, 0);
}

void loop() {
  if (Serial.available() > 0) {
    // read the incoming byte:
    char incomingString = Serial.read();
    Serial.println(incomingString);

    if (incomingString == 43) {
      

      counter *= 5;
      counter = counter>0 ? counter : 1;
      //counter = counter<0 ? -counter : counter;
    } else if (incomingString == 45) {
      
      counter *= 5;
      counter = counter<0 ? counter : -1;
      //counter = counter>0 ? -counter : counter;
    } else {
      antidrift += counter;
      int leftSpeed = antidrift<0 ? 255+antidrift : 255;
      int rightSpeed = antidrift>0 ? 255-antidrift : 255;
      if (counter > 0) {
        Serial.println(antidrift);
        Serial.println(leftSpeed);
        Serial.println(rightSpeed);
        
      }
      
      counter = 0;
      
      
    }

    int leftSpeed = antidrift<0 ? 255+antidrift : 255;
    int rightSpeed = antidrift>0 ? 255-antidrift : 255;

    if (incomingString == 102) { //f=forward
      leftMotor(-leftSpeed);
      rightMotor(rightSpeed);
      delay(300);
      
      leftMotor(-leftSpeed);
      rightMotor(rightSpeed);
    } else if (incomingString == 98) { //b=backward
      leftMotor(leftSpeed);
      rightMotor(-rightSpeed);
    } else if (incomingString == 115) { //s=stop
      leftBrake();
      rightBrake();
    } else if (incomingString == 114) { //right
      leftMotor(leftSpeed);
      rightMotor(rightSpeed);
      delay(50);
      leftBrake();
      rightBrake();
      
    } else if (incomingString == 108) {//left
      leftMotor(-leftSpeed);
      rightMotor(-rightSpeed);
      delay(50);
      leftBrake();
      rightBrake();
    } else if (incomingString == 109) {//move servo
       Serial.println("#SCAN ");
       int counter = -10;
       while (counter < 180) {
        counter += 10;
        readDist(counter, 300);

       }
    } else if (incomingString == 110) {//truncated scan
      Serial.println("#SCAN ");
      int vals[] = {80,90,-1,100,160,170,-1,180};

      for (int i = 0; i < 8; i++) {
        readDist(vals[i], 150);
      }
      
    }
    

  }
  
  delay(10);

}
/*******************************************************************************/
