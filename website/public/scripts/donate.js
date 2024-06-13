const pricingList = [
  {
    price: 10,
    name: 'Steel',
    icon: '🗡️',
    lm_url: 'af5553c6-f5fe-4253-b5d5-eb5531f8dcdf',
  },
  {
    price: 20,
    name: 'Bronze',
    icon: '🗽',
    lm_url: '9d2b0961-d8d2-4b10-94fc-5d7497baef40',
  },
  {
    price: 40,
    name: 'Copper',
    icon: '🎷',
    lm_url: '76d47d46-9ffa-411c-b6c3-96dd491631bc',
  },
  {
    price: 75,
    name: 'Silver',
    icon: '🍴',
    lm_url: 'df45c1e6-49dc-4494-9bdf-071d85e254a5',
  },
  {
    price: 150,
    name: 'Gold',
    icon: '🏆',
    lm_url: '30bf66e8-c9ff-4642-bb39-17a1dfe278f2',
  },
  {
    price: 250,
    name: 'Platinum',
    icon: '🛰',
    lm_url: 'c837df35-eb23-4206-a0b5-024a236077cb',
  },
  {
    price: 500,
    name: 'Sapphire',
    icon: '💍',
    lm_url: '5e5f0b42-b885-4bb6-a981-642d1e40d9ac',
  },
  {
    price: 1000,
    name: 'Diamond',
    icon: '👑',
    lm_url: '5c24c85b-cd08-42ff-9515-743e46f3e825',
  },
]

const priceNumbers = pricingList.map(i => i.price)

const sliderDiv = document.getElementById('support-plans-slider')

const tooltipFormat = {
  to: function (value) {
    const price = pricingList[value]
    const url = `https://support.openfreemap.org/checkout/buy/${price.lm_url}?media=1&desc=0&discount=0`
    return `
        <div class="plan-name">${price.name} Plan</div>
        <div>$${price.price}/month</div>
        <div>
          <a class="plan-link" href="${url}" target="_blank">Subscribe</a>
        </div>
        `
  },
}

const pipFormat = {
  to: function (value) {
    return pricingList[value].icon
  },
}

const pricingSlider = noUiSlider.create(sliderDiv, {
  start: 3,
  range: { min: 0, max: priceNumbers.length - 1 },
  step: 1,
  tooltips: tooltipFormat,
  pips: { mode: 'count', values: priceNumbers.length, format: pipFormat, density: -1 },
})

pricingSlider.on('update', function (values, _) {
  for (const e of sliderDiv.querySelectorAll('.noUi-value')) {
    e.classList.remove('active')
  }

  const value = parseInt(values[0])
  const el = sliderDiv.querySelector('.noUi-value[data-value="' + value + '"]')
  el.classList.add('active')

  const tooltip = sliderDiv.querySelector('.noUi-tooltip')
  tooltip.classList.remove('first')
  tooltip.classList.remove('last')

  if (document.documentElement.clientWidth < 500) {
    if (value === 0) {
      tooltip.classList.add('first')
    }
    if (value === priceNumbers.length - 1) {
      tooltip.classList.add('last')
    }
  }
})

const pips = sliderDiv.querySelectorAll('.noUi-value')
for (const pip of pips) {
  pip.addEventListener('click', e => {
    const v = e.target.getAttribute('data-value')
    pricingSlider.set(v)
  })
}
