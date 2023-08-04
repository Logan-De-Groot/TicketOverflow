import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '1m', target: 1000 },
    { duration: '2m', target: 1500 },
    { duration: '3m', target: 1800 },
    { duration: '4m', target: 2000 }
  ]
};
const API_BASE_URL = 'http://ticketoverflow-681406184.us-east-1.elb.amazonaws.com/api/v1';

function getRandomId() {
  const minId = 1;
  const maxId = 4999;
  const randomId = Math.floor(Math.random() * (maxId - minId + 1)) + minId;
  return `00000000-0000-0000-0000-00000000${randomId.toString().padStart(4, '0')}`;
}

export default function () {
  const userId = getRandomId();

  const getUserResponse = http.get(`${API_BASE_URL}/users/${userId}`, {
    headers: { Accept: 'application/json' },
  });

  check(getUserResponse, {
    'Get user status 200 or 404': (r) => r.status === 200 || r.status === 404,
  });

  sleep(1);
}


