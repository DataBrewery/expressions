++++++++++++++++++++++
Changes in Expressions
++++++++++++++++++++++

Version 0.1.2
=============

* added chance to finalize the compilation object
* back-ported to Python 2.x

Version 0.1.1
=============

New features
------------

* new base class `Dialect` for syntax dialects – will contain list of
  operators and other dialect properties
* added `register_dialect`, `get_dialect` and `unregister_dialect`


Changes
-------

* pass dialect by name, not by structure

Fixes
-----

* fixed compilation of function calls

