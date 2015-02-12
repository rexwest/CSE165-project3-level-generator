# cse165-project3-level-generator
A level generator script and levels for UCSD CSE 165 Project 3  - Space Slalom

Parameters:
- -o: output file
- --debug: enables debug printing
- --wsize: world size
- --wmargin: world edge margin
- --gcount: gate count
- --gwidth: gate width
- --gheight: gate height
-  --pcount: path segment count
- --pcpmin: minimum control points per path segment
- --pcpmax: maximum control points per path segment
- --pcpspread: mamximum amount of directional change from one control point to the next

Sample Usage:  python levelgen.py --gcount 100 --gwidth 5 --gheight 10 --pcount 3 --pcpmin 3 --pcpmax 7 --pcpspread 0.3 -o gen_100_3.txt
