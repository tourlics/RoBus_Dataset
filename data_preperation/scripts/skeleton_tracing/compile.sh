
swig -python trace_skeleton.i
gcc -O3 -c trace_skeleton.c trace_skeleton_wrap.c -I/usr/local/Cellar/python/3.7.6_1/Frameworks/Python.framework/Versions/3.7/include/python3.7m
gcc -O3 -c trace_skeleton.c trace_skeleton_wrap.c -IC:\Program Files\Python36\include

gcc -fPIC -O3 -c trace_skeleton.c trace_skeleton_wrap.c -IC:/msys64/mingw64/include/python3.9

gcc -fPIC -O3 -c trace_skeleton.c trace_skeleton_wrap.c -I'C:/Program Files/Python36/include'

g++ -shared *.o -o _trace_skeleton.pyd -L'C:\Program Files\Python36\libs' -lpython36

gcc $(python3-config --ldflags) -dynamiclib *.o -o _trace_skeleton.so -IC:/msys64/mingw64/lib/libpython3.9.dll.a -undefined dynamic_lookup

# quick tests
# python3 -i -c "import trace_skeleton; trace_skeleton.trace('\0\0\0\1\1\1\0\0\0',3,3); print(trace_skeleton.len_polyline());"
# python3 -i -c "import trace_skeleton; print(trace_skeleton.from_list([0,0,0,1,1,1,0,0,0],3,3))"
# python3 example.py