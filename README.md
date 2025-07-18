# ShapeKey Mimic Blender Addon

**ShapeKey Mimic** is a Blender addon that lets you easily copy the active object's shape key and its keyframes to other mesh objects.

## Features

- **Copy Shape Key**  
  Copies the selected shape key from the active object to other selected mesh objects.  
  If a shape key with the same name exists, you can overwrite it using the Overwrite option.

- **Copy Shape Key Keyframes**  
  Copies shape key animation (keyframes) from the active object to selected target objects.

- **UI Panel**  
  Intuitive panel in 3D View > Tool tab for easy access.

## Installation

1. Download this repository or zip it and install via Blender:  
   `Edit > Preferences > Add-ons > Install...`
2. Enable the `ShapeKey Mimic` addon.

## Usage

1. **Activate the mesh object with the shape key you want to copy**,  
   and **select the target object(s)** as well.
2. Open the **ShapeKey Mimic** panel in the right Tool panel of the 3D View.
3. Select the shape key to copy.
   - Check the `Overwrite` option to overwrite shape keys with the same name.
4.

- Click `Copy Shape Key` to copy the shape key.
- Click `Copy Keyframe` to copy shape key keyframes.

## Panel Overview

- **Shape Keys**: Shows the list and values of shape keys for the current object.
- **Overwrite**: Overwrite shape keys with the same name.
- **Copy Shape Key**: Copy the shape key.
- **Copy Keyframe**: Copy shape key keyframes.

## Notes

- Copying will fail if the source and target objects have different vertex counts.
- The Basis shape key cannot be copied.
- Muted shape keys cannot be copied.

## License

MIT License

---

**Questions & Feedback**  
Feel free to open an issue or

**ShapeKey Mimic**는 Blender에서 활성 오브젝트의 쉐이프키(Shape Key)와 해당 키프레임을 다른 메쉬 오브젝트에 쉽게 복사할 수 있도록 도와주는 애드온입니다.

## 주요 기능

- **쉐이프키 복사**  
  활성 오브젝트의 선택된 쉐이프키를 선택된 다른 메쉬 오브젝트에 복사합니다.  
  이름이 같은 쉐이프키가 이미 있을 경우, Overwrite 옵션으로 덮어쓸 수 있습니다.

- **쉐이프키 키프레임 복사**  
  활성 오브젝트의 쉐이프키 애니메이션(키프레임)을 선택된 타겟 오브젝트에 복사합니다.

- **UI 패널**  
  3D View > Tool 탭에서 직관적으로 사용할 수 있는 패널 제공

## 설치 방법

1. 이 저장소를 다운로드하거나 zip 파일로 압축하여 Blender의 `Edit > Preferences > Add-ons > Install...`에서 설치하세요.
2. `ShapeKey Mimic` 애드온을 활성화하세요.

## 사용법

1. **복사할 쉐이프키가 있는 메쉬 오브젝트를 활성화**하고,  
   **복사 대상 오브젝트(들)**를 함께 선택하세요.
2. 3D View의 오른쪽 Tool 패널에서 **ShapeKey Mimic**을 찾으세요.
3. 복사할 쉐이프키를 선택하고,
   - `Overwrite` 옵션을 체크하면 같은 이름의 쉐이프키를 덮어씁니다.
4.

- `Copy Shape Key` 버튼: 쉐이프키 복사
- `Copy Keyframe` 버튼: 쉐이프키 키프레임 복사

## 패널 설명

- **Shape Keys**: 현재 오브젝트의 쉐이프키 목록과 값을 표시합니다.
- **Overwrite**: 같은 이름의 쉐이프키가 있을 때 덮어쓸지 여부
- **Copy Shape Key**: 쉐이프키 복사 실행
- **Copy Keyframe**: 쉐이프키 키프레임 복사 실행

## 주의사항

- 소스와 타겟 오브젝트의 버텍스 수가 다르면 복사되지 않습니다.
- Basis 쉐이프키는 복사할 수 없습니다.
- 쉐이프키가 음소거(Mute) 상태면 복사할 수 없습니다.

## 라이선스

MIT License

---

**문의 및 피드백**  
이슈나 PR을 통해 자유롭게 의견을 남겨주세요!
