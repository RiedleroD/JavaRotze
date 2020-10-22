#OBJS specifies which files to compile as part of the project
OBJS = main.py 
#CC specifies which compiler we're using
CC = nuitka3
#COMPILER_FLAGS specifies the additional compilation options we're using
COMPILER_FLAGS = --recurse-all --standalone --remove-output --show-progress
#This is the target that compiles our executable
all : $(OBJS)
	$(CC) $(OBJS) $(COMPILER_FLAGS) $(LINKER_FLAGS) 
