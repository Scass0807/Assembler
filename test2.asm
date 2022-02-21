load R2, 1
load R1, 6
load R0, 1
gotolt R1, R2, 8
mul R0, R1, R0
sub R1, R1, 1
goto 4
mv A0, R0
system