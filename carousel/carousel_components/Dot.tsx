import * as React from 'react';
import styled from 'styled-components';

interface StyDotProps {
    chosen: number;
    dotSize: number;
}

const StyDot = styled.li`
    width: ${(props: StyDotProps) => props.dotSize}px;
    height: ${(props: StyDotProps) => props.dotSize}px;
    border-radius: 50%;
    margin-right: ${(props: StyDotProps) => props.dotSize * 0.5}px;
    float: left;
    background: ${(props: StyDotProps) => props.chosen ? 'red' : 'gray'};
`;

interface DotProps {
    chosen: number;
    dotSize: number;
    handleClick: () => void;
}

export default function Dot({ chosen, dotSize, handleClick }: DotProps) {
    return <StyDot chosen={chosen} dotSize={dotSize} onClick={handleClick} />;
}