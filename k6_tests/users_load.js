import http from 'k6/http';
import { sleep, check } from 'k6';
import { Counter } from 'k6/metrics';

const numberOfUsers = new Counter('number_of_users');

function getRandomId() {
    const minId = 1;
    const maxId = 4999;
    const randomId = Math.floor(Math.random() * (maxId - minId + 1)) + minId;
    return `00000000-0000-0000-0000-00000000${randomId.toString().padStart(4, '0')}`;
}
  
export const options = {
  stages: [
    { duration: '1m', target: 1600 },
    { duration: '1m', target: 1600 },
    { duration: '1m', target: 1600 },
    { duration: '1m', target: 1600 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],
  },
};

export default function () {
    const randomUserId = getRandomId();
    const res = http.get(`http://localhost:6400/api/v1/users/${randomUserId}`);
    const a = http.get(`http://localhost:6400/api/v1/users/`);
    check(res, {
        'status is 200': (r) => r.status === 200,
    });
    sleep(1);
}