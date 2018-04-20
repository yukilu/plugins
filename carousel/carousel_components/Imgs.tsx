import * as React from 'react';

import Img from './Img';

interface ImgsProps {
    num: number;
    width: number;
    height: number;
    imgSrcs: string[];
    currentIndex: number;
}

export default function Imgs({ num, width, height, imgSrcs, currentIndex }: ImgsProps) {
    const imgs = [];
    for (let i = 0; i < num; i++) {
        let chosen = 0;
        if (i === currentIndex)
            chosen = 1;
        imgs.push(<Img index={i} key={i} width={width} height={height} imgSrc={imgSrcs[i]} />);
    }

    return (
        <ul style={{ width: num * width, height, position: 'absolute',
            top: 0, left: - currentIndex * width,
            transition: 'left 0.5s ease' }}>
            {imgs}
        </ul>
    );
}