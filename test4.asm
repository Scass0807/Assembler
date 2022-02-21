load R0, 2
load R1, 10
load R2, 1
load R3, 0
gotoeq R3, R1, 9
mul R2, R2, R0
add R3, R3, 1
goto 5
mv A0, R2
system