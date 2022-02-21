load R0, 1
load R1, 0
load R2, 20
gotogt R0, R2, 8
add R1, R1, R0
add R0, R0, 1
goto 4
mv A0, R1
system