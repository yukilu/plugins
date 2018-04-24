# 轮播图组件

## 使用方法
只需要导入轮播图，并传入相应参数即可，示例如下

```ts
import * as React from 'react';
import Carousel from './carousel_components/Carousel';

//render函数中
const imgSrcs = ['/path/0.jpg', '/path/1.jpg', '/path/2.jpg'];
<Carousel num={3} width={600} height={300} imgSrcs={imgSrcs} />
```

## 参数说明
num: 轮播图数量

width: 轮播图宽

height: 轮播图高

imgSrcs: 轮播图图片链接数组，若传入空数组，则默认使用数字作为轮播图内容