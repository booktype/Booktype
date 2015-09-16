/*

sizeof.js

A function to calculate the approximate memory usage of objects

Created by Stephen Morley - http://code.stephenmorley.org/ - and released under
the terms of the CC0 1.0 Universal legal code:

http://creativecommons.org/publicdomain/zero/1.0/legalcode

*/

function sizeof(_1){
var _2=[_1];
var _3=0;
for(var _4=0;_4<_2.length;_4++){
switch(typeof _2[_4]){
case "boolean":
_3+=4;
break;
case "number":
_3+=8;
break;
case "string":
_3+=2*_2[_4].length;
break;
case "object":
if(Object.prototype.toString.call(_2[_4])!="[object Array]"){
for(var _5 in _2[_4]){
_3+=2*_5.length;
}
}
for(var _5 in _2[_4]){
var _6=false;
for(var _7=0;_7<_2.length;_7++){
if(_2[_7]===_2[_4][_5]){
_6=true;
break;
}
}
if(!_6){
_2.push(_2[_4][_5]);
}
}
}
}
return _3;
};
