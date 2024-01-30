const ITEM_ID = 'pro_01hmetcfzgwtjb75msm8sr8snn'

Paddle.Setup({
  token: 'live_69ccb2c84631cfdc44e78975c88',
  eventCallback: function (data) {
    console.log(data)
  },
  // checkout: {
  //   settings: {
  //     displayMode: 'inline',
  //     frameTarget: 'checkout-container',
  //     frameInitialHeight: '450',
  //     frameStyle: 'width: 100%; min-width: 312px; background-color: transparent; border: none;',
  //   },
  // },
})

// Paddle.Checkout.open({
//   items: [
//     {
//       priceId: ITEM_ID,
//     },
//   ],
// })
