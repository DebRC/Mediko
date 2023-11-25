function redirectToOrder(event) {
  const accessToken = localStorage.getItem('accessToken');

  // Check if the access token exists
  if (accessToken) {
    // Get the clicked anchor tag
    var anchorTag = event.target;

    // Get the order ID from the data attribute
    var orderId = anchorTag.getAttribute('data-order-id');

    // Construct the redirect URL
    var redirectUrl = '/myorder/' + accessToken + '/' +  orderId;

    // Redirect to the constructed URL
    window.location.href = redirectUrl;
  } else {
    console.error('Access token not found in local storage');
  }
}
