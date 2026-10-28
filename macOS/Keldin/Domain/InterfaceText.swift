import Foundation

/// Scene commands resolve their copy explicitly because they sit outside the view locale.
enum InterfaceText {
    static func resolve(_ resource: LocalizedStringResource, language: String) -> String {
        String(localized: localizedResource(resource, locale: language == "system" ? .current : Locale(identifier: language)))
    }

    static func localizedResource(_ resource: LocalizedStringResource, locale: Locale) -> LocalizedStringResource {
        var resource = resource
        resource.locale = locale
        return resource
    }
}
