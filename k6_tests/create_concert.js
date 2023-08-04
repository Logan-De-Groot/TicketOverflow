import http from 'k6/http';
import { sleep } from 'k6';


export const options = {
  vus: 40, // Number of virtual users
  duration: '1m', // Duration of the test
};

export default function () {
  const url = 'http://ticketoverflow-571135966.us-east-1.elb.amazonaws.com/api/v1/concerts';
  const payload = JSON.stringify({
    name: 'The Beatles',
    venue: 'The Gabba',
    date: '2023-06-07',
    capacity: 2500,
    status: 'ACTIVE',
  });
  const headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  };
  
  // create a concert
  const res = http.post(url, payload, { headers: headers });
  
  sleep(60);
}