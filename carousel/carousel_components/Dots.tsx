import * as React from 'react';
import styled from 'styled-components';

import Dot from './Dot';

interface StyDotsProps {
    num: number;
    dotSize: number;
}

const StyDots = styled.ul`
    height: ${(props: StyDotsProps) => props.dotSize}px;
    width: ${({ num, dotSize }: StyDotsProps) => 1.5 * dotSize * num}px;
    position: absolute;
    right: 0;
    bottom: ${({ dotSize }: StyDotsProps) => dotSize * 0.5}px;
    opacity: 0.8;
`;

interface DotsProps {
    num: number;
    dotSize: number;
    currentIndex: number;
    setIndex: (i: number) => () => void;
}

export default function Dots({ num, dotSize, currentIndex, setIndex }: DotsProps) {
    const dots = [];
    for (let i = 0; i < num; i++) {
        let chosen = 0;
        if (i === currentIndex)
            chosen = 1;
        dots.push(<Dot chosen={chosen} dotSize={dotSize} key={i} handleClick={setIndex(i)} />);
    }

    return <StyDots num={num} dotSize={dotSize}>{dots}</StyDots>;
}