def facebook_meta_db():
    print("facebook_meta_db")
    payload = {
                "data": [
                    {
                        "action_source": "system_generated",
                        "custom_data": {
                            "event_source": "crm",
                            "lead_event_source": "자금왕 픽셀"
                        },
                        "event_name": "Lead",
                        "event_time": 1673035686,
                        "user_data": {
                            "em": [
                                "7b17fb0bd173f625b58636fb796407c22b3d16fc78302d79f0fd30c2fc2fc068"
                            ],
                            "lead_id": 1234567890123456,
                            "ph": [
                                "6069d14bf122fdfd931dc7beb58e5dfbba395b1faf05bdcd42d12358d63d8599"
                            ]
                        }
                    }
                ]
            }