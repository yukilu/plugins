import * as React from 'react';

import Imgs from './Imgs';
import Dots from './Dots';

interface CarouselProps {
    num: number;
    width: number;
    height: number;
    dotSize: number;
    imgSrcs: string[];
}

interface CarouselState {
    currentIndex: number;
}

export default class Carousel extends React.Component<CarouselProps, CarouselState>{
    interval: NodeJS.Timer;
    constructor(props: CarouselProps) {
        super(props);

        this.state = { currentIndex: 0 };

        this.setIndex = this.setIndex.bind(this);
        this.handleMouseEnter = this.handleMouseEnter.bind(this);
        this.handleMouseLeave = this.handleMouseLeave.bind(this);
    }

    componentDidMount() {
        this.start();
    }

    setIndex(i: number) {
        return () => this.setState({ currentIndex: i });
    }

    start() {
        const { num } = this.props;
        this.interval = setInterval(() => {
            this.setState((prevState, props) => ({ currentIndex: (prevState.currentIndex + 1) % num}));
        }, 2000);
    }

    handleMouseEnter() {
        clearInterval(this.interval);
    }

    handleMouseLeave() {
        this.start();
    }

    render() {
        const { num, width, height, dotSize, imgSrcs } = this.props;
        const { currentIndex } = this.state;
        return (
            <div style={{ width, height, position: 'relative', overflow: 'hidden' }}
                onMouseEnter={this.handleMouseEnter} onMouseLeave={this.handleMouseLeave}>
                <Imgs num={num} width={width} height={height} imgSrcs={imgSrcs} currentIndex={currentIndex} />
                <Dots num={num} dotSize={dotSize} currentIndex={currentIndex} setIndex={this.setIndex} />
            </div>
        );
    }
}