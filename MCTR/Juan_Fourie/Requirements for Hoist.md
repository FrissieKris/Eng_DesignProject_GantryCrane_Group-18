**Hoist Payload with Spooling Mechanism**

Load cell input + brake control interface

ADS1220 vs HX711

2-stage gearbox with COTS DC motor but without worm gear configuration

20kg payload -> 600mm x 400mm x 3mm

support on-hook load to the controller continuously

Active brake engage automatically upon drive power loss or command signal holding the load without drift

1.6m hoist stroke in <= 20s (80mm/s) of 20kg load

1. Hoist gearbox spec and dev — minimum 2-stage gearbox for the spool, driven off EE1's induction motor, no
worm gearbox permitted.
2. Active brake design — fail-safe holding brake satisfying the inherently-safe requirement, its control interface
back to the controller, and selection of its own COTS low-voltage supply rail.
3. On-hook load measurement — load cell in the hoist path, feeding telemetry and interlock use (via an ADS1220
differential channel or a dedicated HX711 on the spare IOs — not yet committed).
4. Dynamics simulation — lift/lower dynamics — load, speed, gear ratio, and brake engagement behaviour —
validating the mechanism against required performance.
5. Controller and safety interface — wiring load cell and brake signals into the controller, and defining interlock
logic tying brake engagement to load and fault conditions

