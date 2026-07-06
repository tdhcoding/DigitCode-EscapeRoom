cmake_minimum_required(VERSION 3.16)
project(DigitCode_SINGLE VERSION 0.1 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD_REQUIRED ON)
find_package(Qt6 REQUIRED COMPONENTS Core Gui Qml Quick WebSockets)
qt_standard_project_setup(REQUIRES 6.10)

qt_add_executable(appDigitCode_SINGLE
    main.cpp
    backend/gameboard.h
    backend/gameboard.cpp
)

qt_add_qml_module(appDigitCode_SINGLE
    URI DigitCode_SINGLE
    VERSION 1.0
    QML_FILES
        UI/Main.qml
        UI/LedDisplay.qml
        UI/LogicButton.qml
        UI/CounterBox.qml
        UI/EODot.qml
        UI/CmpArrow.qml
        UI/BottomBoard.qml
        UI/DraftGrid.qml

        SOURCES backend/hardwareserver.h backend/hardwareserver.cpp
        SOURCES backend/hardwareserver.cpp
        SOURCES backend/hardwareserver.cpp
        SOURCES backend/hardwareserver.cpp
)

set_target_properties(appDigitCode_SINGLE PROPERTIES
    MACOSX_BUNDLE_BUNDLE_VERSION ${PROJECT_VERSION}
    MACOSX_BUNDLE_SHORT_VERSION_STRING ${PROJECT_VERSION_MAJOR}.${PROJECT_VERSION_MINOR}
    MACOSX_BUNDLE TRUE
    WIN32_EXECUTABLE TRUE
)

target_link_libraries(appDigitCode_SINGLE
    PRIVATE Qt6::Core Qt6::Gui Qt6::Qml Qt6::Quick Qt6::WebSockets
)

install(TARGETS appDigitCode_SINGLE
    BUNDLE DESTINATION .
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)