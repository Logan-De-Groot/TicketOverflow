import http from 'k6/http';
import { sleep, group, check } from 'k6';

function getRandomUserId() {
  const minId = 1;
  const maxId = 4999;
  const randomId = Math.floor(Math.random() * (maxId - minId + 1)) + minId;
  return `00000000-0000-0000-0000-00000000${randomId.toString().padStart(4, '0')}`;
}

function createConcert() {
  const payload = JSON.stringify({
    name: 'New Concert',
    date: '2024-01-01',
    venue: 'Some Venue',
    capacity: '250',
    status: "ACTIVE"
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  const res = http.post('http://localhost:6400/api/v1/concerts', payload, params);

  // Check if the response status is 201 (Created) and if the Location header exists
  if (res.status === 200) {
    const location = res.headers['Location'];
    const getRes = http.get('http://localhost:6400/api/v1/concerts'); // Make a GET request to the concert location
    const concerts = JSON.parse(getRes.body);
    const firstConcertId = concerts[0].id;
    console.log(firstConcertId);
    return firstConcertId;
  } else {
    console.log("Failed to create concert");
    return null;
  }

}

function purchaseTicket(concertId, userId) {
  const payload = JSON.stringify({
    user_id: userId,
    concert_id: concertId,
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  return http.post('http://ticketoverflow-571135966.us-east-1.elb.amazonaws.com/api/v1/tickets', payload, params);
}

export const options = {
  stages: [
    { duration: '4m', target: 400 },
    { duration: '4m', target: 800 },
    { duration: '4m', target: 1200 },
    { duration: '4m', target: 1600 },
    { duration: '4m', target: 2000 },
    { duration: '4m', target: 2400 },
    { duration: '4m', target: 2800 },
    { duration: '4m', target: 3200 },
    { duration: '4m', target: 3600 },
    { duration: '4m', target: 4000 },
  ],
};

export default function () {
  const userId = getRandomUserId();

  if (__ITER === 0) {
    group('Create Concert', function () {
      __ENV.CONCERT_ID = "concert:492f248567104e01ad3be9e61cfcb85d"
      sleep(1);
    });
  }

  group('Purchase Tickets', function () {
    const res = purchaseTicket(__ENV.CONCERT_ID, userId);

    check(res, {
      'status is 201':(r) => r.status === 201 || r.status === 412,
    });

    sleep(1);
  });
}