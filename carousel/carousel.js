(function () {
    function Carousel(imgUrl, width, height, parent) {
        var len = imgUrl.length;
        var i, j, temp, img;
        parent = parent || document.body;
        width = width || 800;
        height = height || 600;
        this.imgWidth = width;
        this.imgHeight = height;
        var olWidth = width / 3;
        var btnWidth = olWidth / len * 0.8;
        var btnWidthMargin = olWidth / len * 0.2;
        this.imgUrl = imgUrl;
        var div = document.createElement('div');
        div.id = 'shuffle';
        div.style.width = width + 'px';
        div.style.height = height + 'px';
        div.style.overflow = 'hidden';
        parent.appendChild(div);
        this.element = div;

        var ul = document.createElement('ul');
        ul.style.width = width * len + 'px';
        ul.style.height = height + 'px';
        ul.style.position = 'absolute';
        ul.style.left = ul.style.top = 0;
        for (i = 0; i < len; i++) {
            temp = document.createElement('li');
            img = new Image();
            img.src = imgUrl[i];
            img.style.width = width + 'px';
            img.style.height = height + 'px';
            temp.appendChild(img);
            temp.style.float = 'left';
            ul.appendChild(temp);
        }
        div.appendChild(ul);
        this.imgUl = ul;
        this.img = ul.children;

        var ol = document.createElement('ol');
        ol.style.position = 'absolute';
        ol.style.left = '50%';
        ol.style.bottom = '5%';
        ol.style.marginLeft = -olWidth / 2 + 'px';
        ol.style.width = olWidth + 'px';
        ol.style.height = btnWidth + 'px';
        for (i = 0; i < len; i++) {
            temp = document.createElement('li');
            temp.style.width = temp.style.height = btnWidth + 'px';
            temp.style.backgroundColor = 'white';
            temp.style.borderRadius = '50%';
            temp.style.opacity = 0.6;
            temp.style.marginRight = btnWidthMargin + 'px';
            temp.style.float = 'left';
            temp.style.font = btnWidth * 0.8 + 'px / ' + btnWidth + 'px "Microsoft Yahei"';
            temp.style.textAlign = 'center';
            temp.style.cursor = 'pointer';
            temp.innerHTML = i + 1;
            ol.appendChild(temp);
        }
        div.appendChild(ol);
        this.button = ol.children;
        this.button[0].style.backgroundColor = 'red';
        this.timer = null;

        var that = this;
        for (i = 0; i < len; i++)
            (function (index) {
                that.button[i].addEventListener('click', function () {
                    clearInterval(that.timer);
                    animate(that.imgUl, { left: -index * width }, { time: 500 });
                    for (j = 0; j < len; j++)
                        that.button[j].style.backgroundColor = 'white';
                    this.style.backgroundColor = 'red';
                }, false);
            })(i);
    }

    Carousel.prototype = {
        constructor: Carousel,
        autoplay: function () {
            var i;
            var index = 0;
            var n = 1;
            var len = this.imgUrl.length;
            var that = this;
            this.timer = setInterval(function () {
                index = n++ % len;
                animate(that.imgUl, { left: -index * that.imgWidth }, { time: 500 });
                for (i = 0; i < len; i++)
                    that.button[i].style.backgroundColor = 'white';
                that.button[index].style.backgroundColor = 'red';
            }, 2000);
        }
    };
    window.Carousel = Carousel;

    function animate(element, target, option) {
        option = option || {};
        option.time = option.time || 1000;
        option.duration = option.duration || 30;
        option.easing = option.easing || 'linear';

        var timer = null;
        var n = 1;
        var count = Math.floor(option.time / option.duration);
        var dis = {};
        var start = {};
        var keyStart = 0;
        var current = 0;
        for (var key in target) {
            keyStart = getStyle(element, key);
            keyStart = typeof keyStart === 'undefined' ? 0 : parseFloat(keyStart);
            start[key] = keyStart;
            dis[key] = target[key] - keyStart;
        }
        timer = setInterval(function () {
            for (var key in dis) {
                switch (option.easing) {
                    case 'linear':
                        current = start[key] + n / count * dis[key];
                        break;
                    case 'easing-in':
                        current = start[key] + Math.pow(n / count, 3) * dis[key];
                        break;
                    case 'easing-out':
                        current = start[key] + (1 - Math.pow(1 - n / count, 3)) * dis[key];
                        break;
                    default:
                        console.error(key + ' not found');
                }
                if (key === 'opacity') {
                    element.style.opacity = current;
                    element.style.filter = 'alpha(opacity:' + current + ')';
                }
                else
                    element.style[key] = current + 'px';
            }
            if (n++ === count)
                clearInterval(timer);
        }, option.duration);
    }

    function getStyle(element, property) {
        return (element.currentStyle || getComputedStyle(element, false))[property];
    }
})();
