class rateClass {

    constructor() {
        
    }

    rate(price, comparison_price) {
        return (price - comparison_price) / comparison_price
    }

}

const Rate = new rateClass()

export {
    Rate,
}