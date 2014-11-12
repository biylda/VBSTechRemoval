VBSTechRemoval
==============

Python script for removing specific type of identifiers created by #define directive in C++ files such as
```
#define _SOME_TECHNOLOGY (1 && !_SOME_OTHER_TECHONOLOGY)
```
Note that in my company we use term technology for these identifiers so in the following text I will be calling them that.


# WARNING
I am not liable for any unwanted changes caused by this script, use at your own risk. The script designed
to delete stuff after all. That being said, under the following conditions the script is relatively safe to use:
1. Your project is under revision control.
2. You manually review all of the modification before committing
3. You search the code base for #0# and #1# before committing and modify appropriately! #0# and #1# is what
script uses as temporary replacement of the removed technology and for complicated expression it sometimes fails
to remove it. You can just replace them with 0 and 1 respectively but I rather simplify the expression.

# Usage
```
python removeTechnologyImproved.py <path to project dir> <technology name> <remove or remove !> [DebugFile]
```

## Parameters
1. <path to project dir> is a directory with .cpp .hpp .h .c .hlsl files eg. X:\projectA\src\. Note that it has to walk the whole directory tree and this walk can be quite slow (on TODO list). Therefore I would not suggest calling it on the project root but rather relevant sub folders for bigger projects.
2. <technology name> is the technology you want to remove, ie. _YOUR_TECH
3. <remove or remove !> is either 1 or 0. The former for always on technologies,
0 for always off technologies.
4. [DebugFile] is optional parameter for debugging of what the script does.
It has to be 1 in order to have any effect and in that case it excepts 
<path to project dir> to be a source file not a folder.
ie.  python emoveTechnologyImproved.py ...\sourceFile.cpp _YOUR_TECH 1 1

# Example
```
python removeTechnologyImproved.py X:\projectA\src\ _YOUR_TECH 1
```

# Description

This script removes a specified technology, which is defined as always 1 or always 0 (specified by parameter <remove or remove !> ), 
from c++ files in a specified folder. It can handle simple and nested #if,#else,#elif,#endif,!,#ifdef,#ifndef directives, limited number of && or || and it ignores one line comments.
It works in several stages. First it replaces technology with #0#/#1#, then tries to simplify
the whole directive expressions and finally going through code a removing blocks and directives
resolved to bare minimum (such as #if #0#).

#Background

Coming later.

# TODO list
In no particular order:
1. Improve speed of walking through directory tree
2. Improve ExpressionSimplifier class to be smarter (possibly turn it into full blown parser of directives)
3. Improve FSM classes to allow nested states and better handle various scenarios 
4. Refactoring such as use available FSM implementation
5. Test coverage

