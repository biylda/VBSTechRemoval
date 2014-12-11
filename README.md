VBSTechRemoval
==============

Python script for removing specific type of identifiers created by `#define` directive in C++ files such as
```
#define _SOME_TECHNOLOGY (1 && !_SOME_OTHER_TECHONOLOGY)
```
Note that in my company we use term technology for these identifiers so in the following text I will be calling them that.

Similar to what tools such as Coan or Unidef are doing but written in python and not simplifying anything other than the specified technology.

# WARNING
I am not liable for any unwanted changes caused by this script, use at your own risk. The script is designed
to delete stuff after all. That being said, under the following conditions the script is relatively safe to use:

1. Your project is under revision control.
2. You manually review all of the modification before committing
3. You search the code base for `#0#` and `#1#` before committing and modify appropriately! `#0#` and `#1#` is what script uses as temporary replacement of the removed technology and for complicated expression it sometimes fails to remove it. You can just replace them with 0 and 1 respectively, but I mostly just resolve the expression.

# Usage
```
python VBSTechRemoval.py <path to project dir> <technology name> <remove or remove !> <-d>
```

## Parameters
1. `<path to project dir>` is a directory with .cpp .hpp .h .c .hlsl files eg. X:\projectA\src\.
2. `<technology name>` is the technology you want to remove, eg. _YOUR_TECH
3. `<remove or remove !>` is either 1 or 0. The former for always on technologies, 0 for always off technologies.
4. `<-d>` is optional parameter for debuggin of what the script does (or I should rather say logging). The logs were helpful to me when fixing some issues with this script so I am exposing them here as well. If specified the script excepts <path to project dir> to be a source file not a folder ie. `python VBSTechRemoval.py ..\sourceFile.cpp _YOUR_TECH 1 -d` and it logs everything to `VBSTechRemovalDebug.log`

# Example
```
python VBSTechRemoval.py X:\projectA\src\ _YOUR_TECH 1
```

# Description

This script removes a specified technology, which is defined as always 1 or always 0 (specified by parameter `<remove or remove !>` ), from c++ files in a specified folder. It can handle simple and nested `#if,#else,#elif,#endif,!,#ifdef,#ifndef` directives, limited number of `&&` or `||` and it ignores one line comments.
It works in several stages. First it replaces technology with `#0#` or `#1#`, then tries to simplify
the whole directive expressions and finally going through code a removing blocks and directives
resolved to bare minimum (such as `#if #0#`).

# Test coverage
You can run tests using `python VBSTechRemovalTests.py`

I have provided a set of tests using `unittest` package. It uses files stored in `testfiles\` folder. For each test case there are two files: original code (ending with `_orig`) and expected result of the script (`_exp`). 

# Background

Coming later.

# TODO list in no particular order
* ~~Improve speed of walking through directory tree~~ (done)
* Improve ExpressionSimplifier class to be smarter (possibly turn it into full blown parser of directives)
* Improve FSM classes to allow nested states and better handle various scenarios 
* Refactoring such as use available FSM implementation
* Test coverage (partially done)

