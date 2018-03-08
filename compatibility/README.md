# compatibility
conclude some js compatibilities<br/>

## 0.notes

### 0.1  -  means don't support

### 0.2 old IE means IE5~8

## 1.currentStyle||getComputedByStyle

### 1.1 element.currentStyle

|  chrome  |  firefox  |  IE11~5  
|:--------:|:---------:|:--------:
|    ×     |    ×     |     √   
|    ×     |    ×     |    √    

### 1.2 getComputedStyle(element, false)

|   chrome  |  firefox  |  IE11~9  |  IE8~5
|:---------:|:---------:|:--------:|:-------:
|      √    |     √    |    √     |    ×   

### conclusion:

1. currentStyle is only for IE
2. getComputedStyle for advanced browser

### function:

```js
    function getStyle(obj, sName){
        return (getComputedStyle(obj,false)||obj.currentStyle)[sName];
    }
```

## 2.element.getElementsByClassName(sClass)

|   chrome  |  firefox  |  IE11~9  |  IE8~5
|:---------:|:---------:|:--------:|:--------:
|     √    |     √     |     √    |     ×

### conclusion:

  only for advanced browser

### function:
```js
function getByClassName(obj, sClass){
    if(obj.getElementsByClassName)
        return obj.getElementsByClassName(sClass);
    var elements = obj.getElementsByTagName("*");
    var result = [];
    for(var i=0; i&lt;elements.length; i++){
        var tempArr = elements[i].split(" ");
        for(var j=0; j&lt;tempArr.length; j++)
            if(tempArr[j] == sClass){
                result.push(elements[i]);
                break;
            }
    }
    return result;
}
```

## 3.addEvent

### 3.1 element.addEventListener(sEv, fn, false)

|   chrome   |   firefox  |    IE11  |  IE10~9  | IE8~5
|:----------:|:----------:|:--------:|:--------:|:-----:
|     √     |      √     |      √   |    √     |  ×

### 3.2 element.attachEvent("on"+sEv, fn)

| chrome | firefox | IE11 | IE10~9 | IE8~5
|:------:|:-------:|:----:|:------:|:-----:
|   ×   |    ×    |  ×   |    √   |  √

### conclusion:

1. addEventListener is for advanced browser
2. attachEvent is for old IE

### function:
```js
function addEvent(obj, sEv, fn){
    obj.addEventListener ? obj.addEventListener(sEv,fn,false) : obj.attachEvent("on"+sEv,fn);
}
```

## 4.addMouse

### 4.1 DOMMouseScroll

|   chrome   |    firefox   |    IE11~5
|:----------:|:------------:|:------------:
|     ×     |      √       |      ×

firefox        element.addEventListener("DOMMouseScroll",fn,false)

### 4.2 mousewheel

|   chrome  |   firefox  |  IE11  |  IE10~9  |  IE8~5
|:---------:|:----------:|:------:|:--------:|:--------:
|     √    |     ×      |    √   |     √    |    √

| browser | function 
|:-------:|:----------:
| chrome | element.addEventListener("mousewheel",fn,false)
| IE11   | element.addEventListener("mousewheel",fn,false)
| IE10~9 | element.addEventListener("mousewheel",fn,false)  or  element.attachEvent("onmousewheel",fn)
| IE8~5  | element.attachEvent("onmousewheel",fn)

### conclusion:

1. DOMMouseScroll is only for firefox, and only can use element.addEventListener("DOMMouseScroll",fn,false) to add event
2. mousewheel is for others, chrome and IE11 use addEventListener
3. IE10~9 can use either addEventListener or attachEvent
4. IE8~5 can only use attachEvent
or can use element.onmousewheel = function(){...};

### function:
```js
function addMousewheel(obj,fn){
    if(navigator.userAgent.indexOf("Firefox") != -1)//firfox can only use addEventListener
        obj.addEventListener("DOMMouseScroll",fn_mousewheel,false);
    else
        addEvent(obj,"mousewheel",fn_mousewheel);

    function fn_mousewheel(ev){
        var oEvent = ev || event;
        var dir = true;    //true down, false up
        if(oEvent.detail)
            oEvent.detail>0 ? dir=true : dir=false;
        else
            oEvent.wheelDelta<0 ? dir=true : dir=false;

        fn && fn(dir);
        return false;
    }
}

function fn(dir){
    if(dir)   //true  mouse scroll down
        ...
    else      //false mouse scroll up
        ...
}
```

## 5.mouseScroll

### 5.1 detail

#### 5.1.1 ev.detail

| chrome | firefox | IE11 | IE10~9 | IE8~5
|:------:|:-------:|:----:|:------:|:------:
|   0    | ↓-3 ↑+3 |   0  |    0   |  -

#### 5.1.2 event.detail

| chrome | firefox | IE11 |  IE10~9   IE8~5
|:------:|:-------:|:----:|:--------------:
|   0    |    -    |  0   |    undefined

#### 5.2.1 ev.wheelDelta

|   chrome     |   firefox    |    IE11    IE10~9    IE8~5
|:------------:|:------------:|:----------------------------:
|  ↓-120 ↑+120 | not defined  |     ↓-120 ↑+120     -

#### 5.2.2 event.wheelDelta

|   chrome      |  firefox    |    IE11    IE10~9    IE8~5
|:-------------:|:-----------:|:-----------------------------:
|   ↓-120 ↑+120 |      -      |      ↓-120   ↑+120

### conclusion:

1. firefox use ev.detail, up is negative
2. others use event.wheelDelta or oEvent.wheelDelta, down is negative

## 6. ev||event

### 6.1 ev

|   chrome    |   firefox  |     IE11  |  IE10~9 |   IE8~5
|:-----------:|:----------:|:---------:|:-------:|:----------:
|     √       |     √     |     √     |    √    |      ×

| browser | ev
|:-------:|:----:
| chrome  | object MouseEvent
| firefox | object MouseEvent
| IE11    | object PointerEvent
| IE10~9  | object MouseEvent
| IE8~5   |   undefined

### 6.2 event(window.event)

| chrome | firefox | IE11 | IE10~9 | IE8 | IE7~5
|:------:|:-------:|:----:|:------:|:---:|:-----:
|   √    |   ×    |   √  |   √    |  √  |   √

| browser | event
|:-------:|:------:
| chrome  | object MouseEvent
| firefox | not defined
| IE11    | object PointerEvent
| IE10~9  | object MSEventObj
| IE8     | object Event
| IE7~5   | object

### conclusion:

1. ev for advanced browser
2. window.event is for all except firefox
3. var oEvent = ev || event;

## 7.bubble

#### 7.1.1 event.cancelBubble = true

| chrome | firefox | IE11~5
|:------:|:-------:|:------:
|   √    |   -     |   √

#### 7.1.2 ev.cancelBubble = true

| chrome | firefox | IE11 | IE10~9 | IE8~5
|:------:|:-------:|:----:|:------:|:------:
|   √    |   √    |  √   |   √    |   -

#### 7.2.1 event.stopPropagation()

| chrome | firefox | IE11 | IE10~9 | IE8~5
|:------:|:-------:|:----:|:------:|:------:
|   √    |   -     |  √   |  ×    |  ×

#### 7.2.2 ev.stopPropagation()

| chrome | firefox | IE11 | IE10~9 | IE8~5
|:------:|:-------:|:----:|:------:|:------:
|   √    |   √     |  √  |   √    |   -

### conclusion:

1. when oEvent = ev || event, oEvent.cancelBubble = true is compatible
2. but oEvent.stopPropagation()(use ev.stopPropagation is better) can't support old IE

## 8.preventDefault(to stop default event)

### 8.1 event.preventDefault()

| chrome | firefox | IE11 | IE10~9 | IE8~5
|:------:|:-------:|:----:|:------:|:------:
|   √    |   -     |  √   |  ×    |   ×

### 8.2 ev.preventDefault()

| chrome | firefox | IE11 | IE10~9 | IE8~5
|:------:|:-------:|:----:|:------:|:------:
|   √    |   √     |  √  |   √    |  -

### conclusion:

1. ev.preventDefault() is better than event.preventDefault()

## 9.return false(also to stop default event)

| chrome | firefox | IE11 | IE10~9 | IE8~5
|:------:|:-------:|:----:|:------:|:------:
|   √    |   √     | √   |  √     |   √

### conclusion:

1. it can work in all browsers,but pay attention to return false in addEventListener
2. it won't work in addEventListener, so just use ev.preventDefault() instead
3. but neither addEventListener nor ev.preventDefault can support old IE(5~8)

## 10.delegation

srcElemnt/target (fromElement/relatedTarget  toElement/relatedTarget)

### 10.1 target

#### 10.1.1 event.target

| chrome | firefox | IE11 | IE10~9 | IE8~5
|:------:|:-------:|:----:|:------:|:------:
|   √    |   -     |  √   |  ×    |   ×
|ojbect  HTMLXXElement|ojbect  HTMLXXElement|undefined|undefined|undefined

#### 10.1.2 ev.target

| chrome | firefox | IE11 | IE10~9 | IE8~5
|:------:|:-------:|:----:|:------:|:------:
|  √     |   √     | √   |   √    |    -
|object  HTMLXXElement|object  HTMLXXElement|object  HTMLXXElement|object  HTMLXXElement|   -

### 10.2 srcElement

#### 10.2.1 event.srcElement

| chrome | firefox | IE11  IE10~9  IE8 | IE7~5
|:------:|:-------:|:-----------------:|:------:
|   √    |   -     |       √           |   √
|object HTMLXXElement|-|ojbect HTMLXXElement|object

#### 10.2.2 ev.srcElement

| chrome | firefox | IE11 | IE10~9 | IE8 | IE7~5
|:------:|:-------:|:----:|:------:|:---:|:------:
|   √    |    ×   |   √  |   √    |  -  |   -
| object | undefined| object HTMLXXElement | HTMLXXElement |-|-   

### conclusion:

1. firefox can only use target, but target is not only for firefox
2. fromElement/relatedTarget  toElement/relatedTarget is the same as srcElement/target

### attention:
```js
var oEvent = ev || event;
var oSrc = oEvent.srcElement || target;
```
1. actually, firefox can only use ev.target, old IE can only use event.srcElement
2. chrome and IE11 can use all
3. chrome and IE10~9 can use all except for event.target

## 11.scrollTop

### 11.1 document.documentElement.scrollTop

| chrome | firefox | IE11 | IE10~9 | IE8~5
|:------:|:-------:|:----:|:------:|:------:
|   0    |    √    |  √   |  √    |    √

### 11.2 document.body.scrollTop

| chrome | firefox | IE11 | IE10~9 | IE8~5
|:------:|:-------:|:----:|:------:|:------:
|   √    |   0     |  0   |   0    |   0

### conclusion:

1. document.body.scrollTop is only for chrome
2. document.documentElement.scollTop for others

```js
var scrollTop = document.documentElement.scollTop || document.body.scrollTop;
```
