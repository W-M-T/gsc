SHELL := /bin/bash

compile: $(file)
	./test-codegen.py $(file)
	echo "Succesfully compiled the given SPL source file."

link:
	filename=$(basename $(file) .spl)
	echo $(filename)
	./gsl.py generated/$(filename).splo

run: compile
	FILENAME=basename "test/abc.spl" ".spl"
	echo $(FILENAME)
