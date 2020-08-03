

//This div will display Google map
const mapArea = document.getElementById('map');

//This button will set everything into motion when clicked
const actionBtn = document.getElementById('showMe');

//This will display all the available addresses returned by Google's Geocode Api
const locationsAvailable = document.getElementById('locationList');

//Let's bring in our API_KEY
const __KEY = 'YOUR_API_KEY';

//Let's declare our Gmap and Gmarker variables that will hold the Map and Marker Objects later on
let Gmap;
let Gmarker;

//Now we listen for a click event on our button
actionBtn.addEventListener('click', e => {
  // hide the button
  actionBtn.style.display = "none";
  // call Materialize toast to update user
  console.log("fetching your current location");
  // get the user's position
  getLocation();
});


getLocation = () => {
  // check if user's browser supports Navigator.geolocation
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(displayLocation, showError, options);
  } else {
    console.log("Sorry, your browser does not support this feature... Please Update your Browser to enjoy it");
  }
}

// Displays the different error messages
showError = (error) => {
  mapArea.style.display = "block";
  console.log(error.code);
  switch (error.code) {
    case error.PERMISSION_DENIED:
      mapArea.innerHTML = "You denied the request for your location."
      break;
    case error.POSITION_UNAVAILABLE:
      mapArea.innerHTML = "Your Location information is unavailable."
      break;
    case error.TIMEOUT:
      mapArea.innerHTML = "Your request timed out. Please try again"
      break;
    case error.UNKNOWN_ERROR:
      mapArea.innerHTML = "An unknown error occurred please try again after some time."
      break;
  }
}
//Makes sure location accuracy is high
const options = {
  enableHighAccuracy: true
}

displayLocation = (position) => {
  const lat = position.coords.latitude;
  const lng = position.coords.longitude;
  console.log(lat,lng);
  const latlng = { lat, lng }
  showMap(latlng);
  createMarker(latlng);
  mapArea.style.display = "block";
  getGeolocation(lat, lng)// our new function call
}


showMap = (latlng) => {
  let mapOptions = {
    center: latlng,
    zoom: 17
  };
  Gmap = new google.maps.Map(mapArea, mapOptions);
}


createMarker = (latlng) => {
  let markerOptions = {
    position: latlng,
    map: Gmap,
    animation: google.maps.Animation.BOUNCE,
    clickable: true
  };
  Gmarker = new google.maps.Marker(markerOptions);
}


getGeolocation = (lat, lng) => {
  const latlng = lat + "," + lng;
  fetch( `https://maps.googleapis.com/maps/api/geocode/json?latlng=${latlng}&key=${__KEY}` )
    .then(res => res.json())
    .then(data => console.log(data.results));
}
