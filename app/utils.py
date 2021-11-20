import requests
import re


def get_user_data(username, password):
    session = requests.session()
    data = {
        "client_id": "play-valorant-web-prod",
        "nonce": "1",
        "redirect_uri": "https://playvalorant.com/opt_in",
        "response_type": "token id_token",
    }
    r = session.post("https://auth.riotgames.com/api/v1/authorization", json=data)

    data = {"type": "auth", "username": username, "password": password}
    r = session.put("https://auth.riotgames.com/api/v1/authorization", json=data)
    pattern = re.compile(
        "access_token=((?:[a-zA-Z]|\d|\.|-|_)*).*id_token=((?:[a-zA-Z]|\d|\.|-|_)*).*expires_in=(\d*)"
    )
    if "error" in r.json():
        raise RuntimeError("Login Error!")
    data = pattern.findall(r.json()["response"]["parameters"]["uri"])[0]
    access_token = data[0]

    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    r = session.post(
        "https://entitlements.auth.riotgames.com/api/token/v1", headers=headers, json={}
    )
    entitlements_token = r.json()["entitlements_token"]

    r = session.post("https://auth.riotgames.com/userinfo", headers=headers, json={})
    user_id = r.json()["sub"]

    session.close()
    return access_token, entitlements_token, user_id


def get_currency(entitlements_token, access_token, user_id, region):
    headers = {
        "X-Riot-Entitlements-JWT": entitlements_token,
        "Authorization": f"Bearer {access_token}",
    }
    data = requests.get(
        f"https://pd.{region}.a.pvp.net/store/v1/wallet/{user_id}", headers=headers
    ).json()

    valorant_points = data["Balances"]["85ad13f7-3d1b-5128-9eb2-7cd8ee0b5741"]
    radiant_points = data["Balances"]["e59aa87c-4cbf-517a-5983-6e81511be9b7"]
    return valorant_points, radiant_points


def get_single_skins_data(skin_uuid_list):
    weapons_data = requests.get("https://valorant-api.com/v1/weapons").json()["data"]
    store_offers = requests.get(
        "https://api.henrikdev.xyz/valorant/v1/store-offers"
    ).json()["data"]["Offers"]
    content_tier = requests.get("https://valorant-api.com/v1/contenttiers").json()[
        "data"
    ]
    skin_list = []
    for skin_uuid in skin_uuid_list:
        for weapon in weapons_data:
            for skin in weapon["skins"]:
                if skin_uuid in str(skin):
                    image_url = skin["displayIcon"]
                    if "chromas" in skin:
                        image_url = skin["chromas"][0]["fullRender"]
                    for price_offer in store_offers:
                        if price_offer["OfferID"] == skin_uuid:
                            price = price_offer["Cost"][
                                "85ad13f7-3d1b-5128-9eb2-7cd8ee0b5741"
                            ]
                    for ct in content_tier:
                        if ct["uuid"] == skin["contentTierUuid"]:
                            content_tier_highlight_color = ct["highlightColor"]
                            content_tier_img_url = ct["displayIcon"]
                    skin_list.append(
                        {
                            "name": skin["displayName"],
                            "imgUrl": image_url,
                            "price": price,
                            "contentTierColor": "#" + content_tier_highlight_color,
                            "contentTierImg": content_tier_img_url,
                        }
                    )
    return skin_list


def get_bundle_data(bundle_id_list):
    bundle_list = []
    for bundle in bundle_id_list:
        bundle_data = requests.get(
            f'https://valorant-api.com/v1/bundles/{bundle["DataAssetID"]}'
        ).json()["data"]
        bundle_list.append(
            {
                "name": bundle_data["displayName"],
                "imageUrl": bundle_data["displayIcon"],
                "duration": bundle["DurationRemainingInSeconds"],
            }
        )
    return bundle_list


def get_store_offers(entitlements_token, access_token, user_id, region):
    headers = {
        "X-Riot-Entitlements-JWT": entitlements_token,
        "Authorization": f"Bearer {access_token}",
    }

    skins_data = requests.get(
        f"https://pd.{region}.a.pvp.net/store/v2/storefront/{user_id}", headers=headers
    ).json()

    return {
        "bundleData": get_bundle_data(skins_data["FeaturedBundle"]["Bundles"]),
        "skinsData": get_single_skins_data(
            skins_data["SkinsPanelLayout"]["SingleItemOffers"]
        ),
        "dailyReset": skins_data["SkinsPanelLayout"][
            "SingleItemOffersRemainingDurationInSeconds"
        ],
    }


def get_shop_data(username, password, region):
    access_token, entitlements_token, user_id = get_user_data(username, password)
    data = get_store_offers(entitlements_token, access_token, user_id, region)
    currency_data = get_currency(entitlements_token, access_token, user_id, region)
    data["VP"] = currency_data[0]
    data["RP"] = currency_data[1]
    return data
