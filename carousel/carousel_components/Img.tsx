import * as React from 'react';
import styled from 'styled-components';

interface LiProps {
    width: number;
    height: number;
}

const StyLi = styled.li`
    width: ${(props: LiProps) => props.width}px;
    height: ${(props: LiProps) => props.height}px;
    line-height: ${(props: LiProps) => props.height}px;
    font-size: ${(props: LiProps) => props.height - 10}px;
    text-align: center;
    float: left;
`;

interface ImgProps {
    index: number;
    width: number;
    height: number;
    imgSrc: string;
}

export default function Img({ index, width, height, imgSrc }: ImgProps) {
    let img = null;
    if (imgSrc)
        img = <img src={imgSrc} width={width} height={height} />
    else
        img = index;
    return <StyLi width={width} height={height}>{img}</StyLi>;
}