const knowhowScrapService = (() => {
  const update = async (knowhowId) => {
    const responses = await fetch(`/knowhow-scrap/api/`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json;charset=utf-8',
        'X-CSRFToken': csrf_token
      },
      body: JSON.stringify({'knowhow_id': knowhowId})
    });
    return await responses.json()
  }
  return {update: update}
})()

const tradeScrapService = (() => {
  const update = async (tradeId) => {
    const responses = await fetch(`/trade-scrap/api/`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json;charset=utf-8',
        'X-CSRFToken': csrf_token
      },
      body: JSON.stringify({'trade_id': tradeId})
    });
    return await responses.json()
  }
  return {update: update}
})()

const lectureScrapService = (() => {
  const update = async (lectureId) => {
    const responses = await fetch(`/lecture-scrap/api/`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json;charset=utf-8',
        'X-CSRFToken': csrf_token
      },
      body: JSON.stringify({'lecture_id': lectureId})
    });
    return await responses.json()
  }
  return {update: update}
})()
const postScrapService = (() => {
  const update = async (postId) => {
    const responses = await fetch(`/post-scrap/api/`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json;charset=utf-8',
        'X-CSRFToken': csrf_token
      },
      body: JSON.stringify({'post_id': postId})
    });
    return await responses.json()
  }
  return {update: update}
})()