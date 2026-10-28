# Download owner avatars for repos you don't own; existing files are kept
if ! test -f "repos.json"; then
	printf "Open the repo list first so there are owners to fetch"
	exit
fi

mkdir -p avatars
downloaded=0
while read -r owner url; do
	test -f "avatars/$owner.png" && continue
	curl -sfL "$url&s=128" -o avatars/tmp \
		&& sips -s format png avatars/tmp --out "avatars/$owner.png" > /dev/null \
		&& downloaded=$((downloaded + 1))
done < <(jq -r '.login as $login | [.items[] | select(.owner != $login and .avatar)] | unique_by(.owner)[] | "\(.owner) \(.avatar)"' repos.json)
rm -f avatars/tmp

printf "Downloaded %s new avatars (%s total)" "$downloaded" "$(ls avatars | wc -l | tr -d ' ')"
