import * as React from 'react';
import { render } from 'react-dom';

import Carousel from './carousel_components/Carousel';

const imgSrcs: string[] = [];
for (let i = 0; i < 6; i++)
    imgSrcs.push(`./img/wow${i + 1}.jpg`);

render(<Carousel num={6} width={670} height={335} dotSize={15} imgSrcs={imgSrcs} />, document.getElementById('root'));